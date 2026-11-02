---
name: okr
description: Create, align, check in, and score OKRs at company, team, or personal level - annual and quarterly objectives with measurable key results, parent links up the cascade, weekly check-ins, end-of-period scoring, and the generated OKR tree. Use for "create an OKR", "set team OKRs", "check in on my KRs", "score the quarter", "show the OKR tree", "are we aligned".
---

# OKRs

Method: `System/Frameworks/OKRs.md`. Schema: `type: objective` in `references/schemas.md` (KRs are list items with inline fields and a `^krN` block id).

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Modes (infer from the request)

### create
1. Ask level (company, team, personal), period (`YYYY` annual or `YYYY-Qn`), owner, and team for team level. Default: my team, current quarter.
2. **Parent**: list candidate parents one level up for the same period (annual company KRs for a quarterly company objective; company KRs for a team objective; team KRs for a personal goal) and ask which KR this ladders up to. A company annual objective may have no parent; everything else should.
3. **Draft with the user**. Quality bar, enforce gently:
   - Objective: qualitative, motivating, one line, no numbers.
   - Two to four KRs, each an outcome with a baseline and a target (`from X to Y`), or a milestone with explicit progress. Reframe outputs ("launch X") as outcomes ("X used by N teams").
   - Each KR has an owner. Ambitious targets: 0.7 is a good score.
4. Pick the next free number: count existing objectives for that owner and period (`O1`, `O2`...; personal goals use `G`).
5. `brain new objective --layer <layer> [--team "<Team>"] --title "<Objective>" --set n=<n> --set period=<period> --set owner="[[<Owner>]]" --set parent="[[<Parent objective>#^krN]]"`, then replace the TBD objective and KR lines with the agreed text, keeping `^kr1`, `^kr2` ids.
6. Add the new objective to the parent's `## Supporting objectives` (Dataview does this automatically; check it renders) and `brain refresh`.

### checkin
1. For each KR the user owns (or names): current value and confidence (high, medium, low). Use evidence from the weekly note or a source; otherwise ask. Never estimate a number silently.
2. Update the KR line's `[current:: ]` (or `[progress:: ]` for milestone KRs) and `[confidence:: ]`.
3. Append `| <date> | KRn | <value> | <confidence> | <one-line why> |` to `## Check-ins`. Set `last_checkin:`.
4. Status: compare progress with time elapsed in the period. Behind by more than 30 percent of the expected pace, or confidence low: `at-risk`; far behind with no plan: `off-track`. Tell the user, do not set `off-track` without them.
5. Log the check-in in my weekly note under `## KR check-ins`. `brain refresh`.

### score (end of period)
Final value per KR, score 0.0 to 1.0, write `## Retrospective` (what worked, what we learned, what carries over), set `status: done` (or `dropped` with a reason). Carry-over KRs become new objectives next period with this one linked.

### tree / align
`brain refresh`, then show `Company/OKRs/OKR Tree - <quarter>.md` (shared) or `Personal/Goals/My OKR Tree - <quarter>.md` (with my goals). Report the "Not aligned" list and objectives whose parent is not an objective note, and suggest parents.

## Rules
- Team objectives live in `Teams/<Team>/OKRs/`, company ones in `Company/OKRs/`, personal goals in `Personal/Goals/` (never shared; they may link up to team KRs).
- Changing a company objective is a shared, high-visibility edit: show the diff first, and with `sharing: git` suggest a pull request.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
