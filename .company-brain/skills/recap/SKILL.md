---
name: recap
description: Summarize a period from the brain - today, this week, this month, or this quarter - what I worked on, decisions taken, key results that moved, cards finished, meetings and people, ideas captured, and open threads, as a short narrative with links and the questions the period's notes could answer next. Use for "recap my week", "what did I do this month", "summarize the quarter", "catch me up", before a 1:1 or a review.
---

# Recap

Read-only. A narrative of a period, built from the notes, not from memory. For the weekly note itself use `weekly`; for a team roll-up use `team-weekly`; for scoring a quarter use `okr` or `plan`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Pick the period** from the argument: `today`, `week` (default), `month`, `quarter`, or two dates. Run `brain period` (with `--date` for another day) for the ISO week, quarter, and file names; do not compute dates by hand.
2. **Collect the notes in range**, by their `date` field or filename date:
   - my daily notes (`Personal/Daily/`) and weekly notes (`Personal/Weekly/`);
   - meetings I attended (`*/Meetings/`, `Personal/1-1s/` entries in range);
   - decision records in any layer (`*/Decisions/DEC-<date> - ...`);
   - cards finished in range (`✅ <Mon DD>` in `## ✅ Done` of `Personal/My Board.md` and my team boards);
   - KR check-in rows in range in the objectives I or my teams own, and status-log rows in my projects;
   - ideas and knowledge notes created in range (`Personal/Notes/`, my teams' `Knowledge/`);
   - for `month` or `quarter`, my teams' weekly notes (`Teams/<Team>/Weekly/`).
   For a month or a quarter, the notes can be read in parallel by subagents, one per week, each returning facts with the note they came from.
3. **Synthesize**, do not dump: a few short paragraphs or grouped bullets covering what I worked on and why (linked to the KRs it moved), decisions and who took them, KR movement (start and end value for the period), what was finished, who I worked with, ideas captured, and what is still open or overdue. Every claim carries the `[[note]]` it came from.
4. **Gaps**: name days or weeks with no notes, and KRs I own with no check-in in the period. Do not fill gaps with guesses.
5. **End with "Suggested questions for future agent"**: 4 or 5 questions this period's notes are well placed to answer that the user has not asked, each citing at least one `[[note]]`. Prefer tensions between notes, people or projects that appeared together but are not linked, and next actions the period implies. Avoid generic ones ("what did I work on?").
6. Offer to save: the week into the weekly note (`weekly` skill), or any recap as a personal knowledge note. Write nothing unless the user says yes.

The recap is personal by default: it may read my Personal notes. If the user wants to share it, write a sanitized version through `promote`, never a link to a Personal note.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
