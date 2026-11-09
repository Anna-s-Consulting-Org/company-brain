---
name: promote
description: Share a personal note with the team or company - builds a sanitized copy (no Private sections, no links to personal notes, no personal-only fields), shows the diff, writes it in the target layer, and links back up from the personal note; also promotes team notes to the company layer. Use for "share this with the team", "publish this", "promote to company", "make this a team note".
---

# Promote

The only path from Personal/ to a shared layer. Spec: `references/layers.md` (Promotion). Nothing is promoted without the user's explicit yes.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Source and target**: the note to share (personal or team) and the target layer and team. Ask if not stated.
2. **Type and place**: keep the type when it exists in the target layer (decision, meeting, project, knowledge); a personal weekly becomes a `team-update`; a personal goal becomes a draft team objective proposal (handled by `okr` create, with the team lead).
3. **Build the shared version** with `brain promote "<note path>" --to team|company [--team "<Team>"] [--kind <kind>] [--name "<stem>"]`. Without `--yes` it is a dry run that writes nothing and prints what was removed plus the diff. It:
   - drops every `## Private` section;
   - rewrites every link to a Personal/ note as plain text (keeps the words, drops the brackets);
   - removes personal-only fields (`energy`, `mood`, `promoted_to`, the `private` tag), sets `layer:` and `team:`, keeps `date`;
   - turns a personal weekly into a team update built from its `## Team update` draft only;
   - refuses `me`, daily, 1:1, and personal-goal notes, and names that already exist in a shared layer.
4. **Review the dry run yourself** for anything the user would consider private that is not under `## Private` (candid remarks, names, quotes from private messages). Propose edits to the personal note, or `--name`, and re-run the dry run.
5. **Show the user the diff** and wait for an explicit yes.
6. **Write**: re-run the same command with `--yes`. It writes the shared note, adds `promoted_to: "[[<shared note>]]"` to the source (an upward link, allowed), and runs the layer check on the result; fix anything it reports.
7. **Preamble**: rewrite the shared note's `## For future agent` preamble for the shared audience (team updates already get one from their template). Do not record the personal note's path anywhere in the shared note.
8. Say how the note reaches teammates: with `sharing: drive` or `folder` it syncs as soon as it is written; with `local` it stays on this machine until `brain share` links `Company/` and `Teams/` to a shared folder. Never commit it to git.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
