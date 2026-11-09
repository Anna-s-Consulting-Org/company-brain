---
name: find
description: Search the brain and return results with context, not just filenames - title, layer, type, owner, status, date, and the excerpt that matches - grouped by type, with synonyms tried when results are thin and stale or draft notes flagged. Use for "find", "search the brain", "where is", "do we have a note on", "what do we know about".
argument-hint: "<query>"
---

# Find

Read-only. Finds notes and explains what each one is, so the user can act on the results without opening every file.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Read the query** from the argument. With no argument, ask what to find. Strip filler words; keep names, titles, and terms of art.
2. **Search.** Run `brain search "<query>" --limit 15` (keyword ranking, plus semantic search when an index is available; `--lexical` forces keyword only). With the brain MCP server connected, `brain_search` gives the same results. For an exact phrase, a name, or a number, also `grep -rilF "<phrase>"` across `Company/`, `Teams/`, and `Personal/` (`-F` matches the text literally, so `C++`, `$1.2M` or `[[Jane Doe]]` work). Check `index.md` for titles and aliases.
3. **Widen when thin.** Fewer than three good hits: try synonyms and related terms (customer and client, OKR and objective and key result, the team's name and its lead), the singular and plural, and the note-name prefixes (`OPP - `, `SOL - `, `DEC-`). Say which variants you tried.
4. **Read the top hits** far enough to describe them: frontmatter (`type`, `layer`, `team`, `owner`, `status`, `date`, `updated`, `last-checked`) and the part that matches.
5. **Answer** grouped by type (strategy and OKRs, discovery, projects, decisions, meetings, people and teams, knowledge, personal). For each result: `[[Note title]]`, path, layer, owner and status when set, the date, and a one or two line excerpt that shows why it matched. Flag notes that are `status: draft` (not agreed), superseded decisions (`superseded_by`), and facts with an old `as of` stamp or no `last-checked`.
6. **Offer the next step**: open a note, update it, link it from another, or hand off to the skill that owns it (`okr`, `project`, `decide`, `reconcile` when two results disagree).

Before saying nothing exists, search the filename, aliases, `index.md`, and the full text, and say what you searched. Notes in `Personal/` are the user's own; show them only to that user, and never cite them in a shared note.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
