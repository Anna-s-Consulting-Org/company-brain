---
name: challenge
description: Red-team an idea, plan, or belief against the brain's own history - the strategy and its guiding policy, Playing to Win choices, past decisions and the options they rejected, experiment results, OKRs, prioritization scores, and meeting notes - with every piece of counter-evidence quoted and linked, then a verdict. Use for "challenge this", "poke holes in", "devil's advocate", "red team this plan", "are we sure about", before a decision or a planning cycle.
---

# Challenge

The point is to pressure-test, not to agree. The brain remembers what the company already decided, tried, and learned; this skill holds a new position against it. Evidence is quoted word for word from notes, or it does not count.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **State the position.** Take the idea, plan, or belief from the argument; with no argument, take the user's current position from the conversation and restate it in one or two sentences. Ask only if it is truly unclear.
2. **List its premises**: the 3-6 things that must be true for it to be right (about customers, the market, capacity, cost, timing, what was tried before).
3. **Search for counter-evidence** in parallel (subagents work well here), each returning note path, line, and the exact line quoted:
   - **Strategy fit**: `Company/Strategy/` and the team's `Strategy/`: does it follow the guiding policy, the where-to-play and how-to-win choices, the values? Does it fall into a choice the strategy rejected?
   - **Decisions**: `*/Decisions/`: past decisions on the same question, the options they rejected and why, and any `supersedes` chain.
   - **Discovery**: `*/Discovery/`: experiments (`EXP - `) whose results bear on a premise, opportunities with contrary evidence, solutions scored low on impact or high on effort.
   - **OKRs and priorities**: does it serve a current key result (`brain context --level 1`)? What would it displace on the roadmap or the board?
   - **Meetings and knowledge**: risks someone raised, lessons learned, sources that say otherwise.
4. **Prove every quote** before using it:
   ```bash
   python3 "<engine>/scripts/verify_quotes.py" --path "<brain>" <<'JSON'
   [{"path": "<note path>", "line": 12, "quote": "<line copied from that note>"}]
   JSON
   ```
   Drop any quote that does not come back `"ok": true`; use `found_line` from the output.
5. **Write the red-team analysis**:
   - **Position**: the claim, restated.
   - **Premises**: each one marked supported, contradicted, or untested by the brain.
   - **Counter-evidence**: each item a verbatim quote with `[[note]]`, date, and who said or decided it.
   - **Fit with strategy and OKRs**: which choice or key result it serves or works against.
   - **Blind spots**: what the brain's history suggests is being ignored.
   - **Cheapest test**: for each untested premise, the smallest experiment that would settle it.
   - **Verdict**: consistent with what the company knows, proceed with care, or contradicted. If the search found nothing against it, say so plainly and list what you searched.
6. **Log it** in today's daily note under `## Notes and captures`: `- Challenged: <position, short>, verdict <verdict>`.
7. **Offer to keep it**: as a personal knowledge note (`Personal/Notes/Challenge - <Title>`), as considerations in a pending decision record (`decide`), or as assumption-test experiments (`ost`). Write nothing shared unless the user says yes.

Do not soften the findings, and do not invent risks the brain does not support: an opinion of yours is labelled `speculation`, separate from the quoted evidence.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
