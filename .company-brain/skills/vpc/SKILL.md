---
name: vpc
description: Create or update a Value Proposition Canvas for a customer segment - customer jobs, pains, and gains from evidence, the value map (products and services, pain relievers, gain creators), fit assessment, and assumptions to test as experiments. Use for "value proposition canvas", "VPC for <segment>", "customer jobs pains gains", "do we have product market fit with <segment>".
---

# Value Proposition Canvas

Theory: `System/Frameworks/Value Proposition Canvas.md`. One canvas per segment: `<layer>/Strategy/VPC - <Segment>.md`.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Segment**: name it concretely (role, company type, situation). Check for an existing `VPC - ...` note first and update it instead of creating a second.
2. **Evidence**: collect customer meetings, interview notes, support themes, research knowledge notes, call summaries (any connected source the user has, for example a customer-calls analytics tool), and opportunity notes in discovery. Link each item in `evidence:`.
3. **Customer profile** (left side). Fill the tables in `## Customer jobs`, `## Pains`, `## Gains`:
   - Jobs: functional, social, emotional; importance 1-5.
   - Pains: undesired outcomes, obstacles, risks; severity 1-5.
   - Gains: required, expected, desired, unexpected; relevance 1-5.
   - Each row cites evidence. A row with no evidence is marked `hypothesis` in the Evidence column.
4. **Value map** (right side): `## Products and services`, `## Pain relievers` (each names the pain it relieves), `## Gain creators` (each names the gain).
5. **Fit**: which top pains and gains are covered, which are gaps, and the fit stage (`none`, `problem-solution`, `product-market`, `business-model`). Set `fit:` and `status:` (`hypothesis` while most rows lack evidence).
6. **Assumptions to test**: the riskiest beliefs in the canvas. For each, offer to create an experiment in discovery via the `ost` skill, and gaps as opportunities.
7. Link the canvas from the strategy note (`strategy:` field) and `brain index`.

Never invent customer jobs, pains, or quotes. If there is no evidence yet, say so and produce a hypothesis canvas plus an interview plan.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
