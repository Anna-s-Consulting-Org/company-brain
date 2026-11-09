---
name: team-weekly
description: Roll up a team's week - collects every member's published team update, KR progress versus last week, board movement, team meetings and decisions; writes the team weekly note and flags missing updates, risks, and decisions needed. Use for "team weekly", "roll up the team updates", "team status", "prepare the team sync".
argument-hint: "[team]"
---

# Team weekly

Written by the team lead (or whoever runs it) into `Teams/<Team>/Weekly/<YYYY>-W<WW> - <Team> - Team Weekly.md`. Reads only shared notes; never reads other people's Personal/ (it is not there).

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. Pick the team (default: my home team) and week (`brain period`).
2. **Collect**:
   - Member updates: notes with `type: team-update` and this `week` in `Teams/<Team>/Weekly/`.
   - Members: people whose profile `team:` is this team. List members with no update as "missing" (state it neutrally; do not chase).
   - Objectives: the team's objectives for the quarter, KR values now, and the KR values in last week's roll-up (for a trend arrow: up, flat, down).
   - Board: cards moved to Done this week, overdue cards, cards in Waiting.
   - Team meetings and decisions dated this week.
3. **Write**: `brain new team-weekly --layer team --team "<Team>" --set 'contributors=["[[A]]", "[[B]]"]'`, then fill: a three-sentence summary for outsiders, the KR status table, highlights, risks and blockers, decisions needed (with who decides), next week's focus. Link each member update under `## Updates`.
4. **Escalate**: KRs with falling confidence or no check-in for two weeks go under Risks; cross-team dependencies go to Decisions needed with the other team linked.
5. **Optional, ask first**: draft (do not send) a Slack post of the summary for the team channel (`slack` in the team charter) using a draft tool if available. Sending messages is outward-facing: only with explicit approval.
6. `brain refresh` so the OKR tree shows the latest values.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
