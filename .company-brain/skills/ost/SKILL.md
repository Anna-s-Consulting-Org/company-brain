---
name: ost
description: Build and maintain opportunity solution trees (Teresa Torres) - an outcome tied to a key result, customer opportunities with evidence, candidate solutions with impact and effort, and assumption-test experiments; renders Mermaid trees and Obsidian canvases. Use for "opportunity solution tree", "OST", "discovery", "add an opportunity", "what solutions do we have for", "plan an experiment".
argument-hint: "[outcome or node]"
---

# Opportunity solution tree

Theory: `System/Frameworks/Opportunity Solution Tree.md`. Nodes are notes in `<layer>/Discovery/`: `OUT -`, `OPP -`, `SOL -`, `EXP -`, linked by `parent:`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Modes
- **start**: pick the KR (list the layer's current KRs). `brain new outcome --layer <l> [--team T] --title "<outcome>" --set kr="[[<objective>#^krN]]" --set metric="<metric>"`.
- **add opportunity**: `brain new opportunity ... --title "<customer need in their words>" --set parent="[[OUT - ...]]"` (or a parent opportunity for a sub-opportunity). Fill evidence and sizing.
- **add solution**: `brain new solution ... --title "<solution>" --set parent="[[OPP - ...]]" --set impact=<1-5> --set effort=<1-5>`. Fill the scoring rationale.
- **add experiment**: `brain new experiment ... --title "<test>" --set parent="[[SOL - ...]]" --set assumption="<assumption>" --set assumption_type=<desirability|viability|feasibility|usability|ethical>`. Success criteria are written before the test runs.
- **review**: `brain refresh`, then read the hub (`Company Discovery` or `<Team> Discovery`) and the canvas `OST - <outcome>.canvas`. Report gaps.
- **record result**: set `result:` on the experiment, write the data, and update the solution (`status: validated`, changed, or `dropped`).

## Quality checks (apply on every change)
- An opportunity is a customer need, pain, or desire, never a feature. "Users need a dashboard" is a solution in disguise: ask what need it serves.
- Opportunities need evidence (linked interviews, tickets, data). No evidence: keep it, set confidence to speculation, and propose research.
- Compare and contrast: aim for at least three solutions for the target opportunity before committing to one.
- A solution is not `validated` without at least one passed experiment on its riskiest assumption.
- Keep the tree shallow and readable: split broad opportunities into sub-opportunities.

## Propagate
- Scored solutions feed `prioritize`; validated or planned ones feed `roadmap` (`roadmap: now|next|later`) and, when work starts, a `project` with `solution:` linked.
- `brain refresh` after every change so the Mermaid tree and canvas match the notes. The canvas cards are the real notes, so editing a card edits the note.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
