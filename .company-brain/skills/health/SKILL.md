---
name: health
description: Check and repair the brain - layer leaks (shared notes linking to personal ones), AI-first frontmatter and preambles, layer mismatches, unaligned or stale OKRs, KRs without owners, orphan notes, unresolved links, missing Obsidian plugins; then rebuild every generated view. Use for "brain health", "check the brain", "fix the vault", "why is the graph messy", before a quarterly review or a git commit.
---

# Health

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. `brain check` (add `--json` to parse). Severity: error (leaks, layer mismatches, Private sections in shared notes), warn (missing AI-first fields or preamble, unaligned objectives, missing KRs, stale check-ins), info (orphans, unresolved links, KRs without owners). Freshness findings come through `check` too: FRESH-1 (an undated claim about a fast-changing fact) and FRESH-3 (unmapped pointer) as warn, FRESH-2 (aged stamp) and FRESH-5 (unused suppression) as info; `brain freshness` lists only those.
2. **Fix errors first**, showing each change:
   - Leak: rewrite the link as plain text, or promote the target with `promote` if it should be shared.
   - Layer mismatch: move the note to the folder of its real layer, or correct `layer:` (ask which is right).
   - Private section in a shared note: move that section into a personal note and remove it from the shared one.
3. **Warnings**: add missing frontmatter and preambles (derive from the content, never invent facts); propose parents for unaligned objectives; nudge stale check-ins (list them with owners; do not check in on someone else's behalf).
4. **Freshness**: for each FRESH finding, re-observe the fact from its source and add `(as of YYYY-MM-DD)`, or convert it to a pointer (where the truth lives, plus the last observed value with a stamp), or move it into a dated note. Never delete a claim to silence the lint, and never invent a number (`.company-brain/references/freshness-policy.md`).
5. **Hook-less checks**: if notes were written by something with no hook runtime (a cron agent, a script, another tool), run `python3 "<engine>/scripts/check_notes.py" --path "<brain>" --changed --fix` first; it applies the same AI-first check the write hook runs and exits 1 on anything it cannot fix.
6. **Info**, offered as one batch: link orphans from their hub; create stubs for wanted notes in the right layer (never in Personal/ for a link from a shared note); fill KR owners.
7. **Obsidian**: check `.obsidian/plugins/` for dataview, obsidian-kanban, templater-obsidian, calendar and say which are missing.
8. `brain refresh`, then `brain check` again and report before and after counts.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
