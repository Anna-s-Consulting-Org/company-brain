---
name: strategy
description: Draft or revise mission, vision, values, and strategy - Rumelt strategy kernel (diagnosis, guiding policy, coherent actions), Playing to Win choice cascade, and Business Model Canvas - grounded in existing notes, sources, and research. Use for "write our mission", "draft a vision", "define values", "what is our strategy", "strategy kernel", "where to play how to win", "business model canvas".
---

# Strategy

Theory notes: `System/Frameworks/Strategy Kernel.md`, `Playing to Win.md`, `Business Model Canvas.md`. Customer fit per segment is the `vpc` skill.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Modes
| Mode | Writes |
|---|---|
| mission, vision, values | `Company/Mission.md`, `Vision.md`, `Values.md` (edit in place, add a revision-history row) |
| kernel | `brain new strategy --title "<horizon, e.g. YYYY-YYYY>" --set horizon=<h>` |
| playing-to-win | `brain new playing-to-win --title "<name>" --set horizon=<h>` |
| bmc | `brain new bmc --title "<business or product>"` |

Team-level strategy (rare): add `--layer team --team "<Team>"`.

## Steps
1. **Gather before drafting**: existing purpose and strategy notes, the latest annual plan, knowledge notes, decisions, relevant mounted sources, and (if available) company search such as Glean for official strategy documents. List what you used with dates. Missing inputs are TBD, not invented.
2. **Ask, one question at a time**, the few questions the framework needs:
   - Mission: who do we serve, what change do we make, how is it different?
   - Vision: in N years, what is observably true for customers and for us?
   - Values: which behaviours decide real trade-offs? What do we give up for each?
   - Kernel: what is the critical challenge (diagnosis)? What approach rules options out (guiding policy)? Which coordinated actions follow?
   - Playing to Win: winning aspiration, where to play and not play, how to win, capabilities, management systems.
3. **Draft** in the note's sections, citing sources inline. Offer two alternative phrasings where wording matters (mission, vision).
4. **Check** with the framework's own test (kernel: the bad-strategy checklist; Playing to Win: each choice reinforces the next; values: each implies a trade-off).
5. **Connect**: coherent actions become annual objectives (`okr`), projects, or decisions; link them both ways. Link the relevant VPCs.
6. Status stays `draft`. Set `status: approved` and `approved_by:` only when the user says it was approved, and record who approved it.

Mission, vision, values, and strategy are company-wide statements: show the full diff before saving changes to an approved version.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
