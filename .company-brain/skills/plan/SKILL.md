---
name: plan
description: Run the annual or quarterly planning cycle - review and score the last period, revisit mission, vision, and strategy, set annual then quarterly objectives that cascade to teams, choose discovery focus, prioritize, update the roadmap, and write the Annual or Quarterly Plan note with the operating cadence. Use for "annual planning", "quarterly planning", "plan Q1", "set next quarter".
argument-hint: "[annual | quarterly]"
---

# Plan

Orchestrates other skills; the plan note (`type: plan`) records the choices. Company plans in `Company/Planning/`, team plans in `Teams/<Team>/Planning/`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Quarterly (default)
1. **Score last quarter**: run `okr` score for every objective in the previous quarter at this layer. Fill the plan's `## 1. Last quarter` table with scores and one lesson each.
2. **Context**: `context` level 2. Note what changed (new knowledge notes, decisions, team changes) since the last plan.
3. **Draft objectives**: company plan: three to five quarterly company objectives, each laddering up to an annual company KR. Team plan: two to four team objectives, each laddering up to a company KR. Create each with `okr` create once the user agrees.
4. **Discovery focus**: for each KR that needs discovery, start or update an opportunity solution tree with `ost` (outcome node linked to the KR).
5. **Prioritize**: run `prioritize` for the layer; record which quick wins go to Now and how big bets are sliced.
6. **Roadmap**: run `roadmap` to move cards between Now, Next, and Later.
7. **Cadence**: set check-in rhythm, mid-quarter review date, scoring date. Offer to add them to the calendar (ask first; creating events is outward-facing).
8. **Write**: `brain new quarterly-plan --layer <layer> [--team T] --set period=<YYYY-Qn>` and fill each section with links. Status `draft` until the user says it is committed.

## Annual
1. Score the year (annual objectives) and summarize the four quarterly retrospectives.
2. Revisit `[[Mission]]`, `[[Vision]]`, `[[Values]]` and the current strategy with `strategy` (kernel diagnosis first: has the challenge changed?). Refresh value proposition canvases with `vpc` for segments that matter next year.
3. Set three to five annual company objectives with `okr` create (period `YYYY`, no parent).
4. Big bets and stop-doing list, organization changes (`org`), quarter-by-quarter shape.
5. `brain new annual-plan --set period=<YYYY>` and fill.

## Rules
- Plans are proposals until committed: present drafts in chat, write the plan note with `status: draft`, switch to `committed` only on the user's word.
- Never create OKRs for another team without its lead; draft them as proposals in the team plan instead.
- Finish with `brain refresh` and a one-screen summary: objectives, discovery focus, Now column, dates.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
