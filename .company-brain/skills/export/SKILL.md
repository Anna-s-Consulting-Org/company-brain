---
name: export
description: Export the shared company and team layers as a read-only Claude Project pack (condensed markdown files plus project instructions) for colleagues who use claude.ai chat or mobile instead of Claude Code. Use for "export to a Claude project", "make a project pack", "share the brain with claude.ai", "update the project knowledge".
---

# Export

The pack never contains Personal/ or Sources/. It is a snapshot: edit the vault, then re-export.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. `brain refresh` so generated views (OKR tree, discovery, matrix, org chart) are current.
2. `brain check --severity error`. Do not export while there are leak errors; fix them first with `health`.
3. `brain export-pack` (default output `Exports/Claude Project/`, gitignored; `--out <dir>` for another place). It writes grouped files (company overview, strategy, OKRs, org and teams, discovery and roadmap, projects, decisions, recent team roll-ups) and `PROJECT_INSTRUCTIONS.md`.
4. Report the files and total size. Tell the user how to use it:
   - claude.ai: Projects, New project, paste the text from `PROJECT_INSTRUCTIONS.md` into the project instructions, upload the other files as project knowledge. On a Team or Enterprise plan the project can be shared with colleagues.
   - Re-export after planning cycles or monthly, and replace the files in the project.
5. Remind once: the pack contains internal company information; share the project only inside the company.

## Claude Desktop chat (optional)
For read and write access from the Claude Desktop chat (not Cowork), the brain MCP server can be added to Claude Desktop's MCP config: command `uv`, args `run --no-project --with mcp<2 python <engine>/mcp/vault/server.py`, env `COMPANY_BRAIN_PATH=<brain>`. Show the user the snippet with their paths; do not edit their config file without asking.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
