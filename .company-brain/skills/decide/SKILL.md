---
name: decide
description: Record a decision in the right layer - the decision, context, options considered, reasoning, consequences, who decided, and what it supersedes; links it from the meeting, project, or OKR it affects. Use for "we decided", "record this decision", "log a decision", "ADR", "why did we decide".
---

# Decide

Schema: `type: decision`. Folder: `<layer>/Decisions/DEC-<YYYY-MM-DD> - <Title>.md`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Record
1. Layer: the layer of what was decided (a team process: team; strategy, pricing, org: company; my own working choice: personal).
2. Search first: an existing decision on the same topic is updated or superseded, not duplicated.
3. `brain new decision --layer <l> [--team T] --title "<short title>" --set context="[[<meeting, project, or OKR>]]" --set 'decided_by=["[[A]]"]' --set status=<proposed|accepted>`.
4. Fill: the decision in one active sentence, context, options with pros and cons, reasoning, consequences (what changes, accepted costs), review date if any.
5. Supersedes: set `supersedes:` here, and on the old decision set `status: superseded` and `superseded_by:`.
6. Propagate: add a line to the context note's `## Decisions`, and to the affected project, objective, or roadmap card.

## Recall ("why did we...")
Search decisions by topic across layers I can read, follow `supersedes` chains to the current one, and answer with the decision note linked and its status.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
