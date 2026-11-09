---
name: connect
description: Connect folders from the Desktop or Google Drive to the brain as read-only sources (symlinks under Sources/), share mounts with teammates through brain.yaml, recreate shared mounts on a new machine, and resolve Google Docs pointer files. Use for "connect my desktop folder", "link Google Drive", "add a source", "mount the strategy folder", "sync sources".
argument-hint: "[folder]"
---

# Connect

Spec: `references/sources.md`. Mounts live in `Sources/` (gitignored, machine-local); shared mounts are recorded in `brain.yaml` in a portable form.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Discover**: `brain sources` shows current mounts and detected Google Drive accounts (`~/Library/CloudStorage/GoogleDrive-<account>/` with `My Drive/` and `Shared drives/`). If the user names a folder loosely, list candidates on the Desktop or in Drive and confirm the exact path.
2. **Mount**: `brain connect "<absolute path>" --name "<Short Name>"`. Add `--shared` when the folder is a shared location teammates also have (a Shared Drive, a team folder); it records a portable entry in `brain.yaml`.
3. **Teammates**: after cloning, `brain connect --sync` recreates every shared mount against their own Desktop and Drive and reports what is missing on their machine.
4. **Explain** in one line each: files are read in place and never modified; Obsidian indexes mounted folders (mount specific folders, not a whole drive); Google Docs, Sheets, and Slides appear as `.gdoc` pointers whose content is read through the Google Drive connector.
5. **Offer to ingest** the most relevant files with the `ingest` skill.

## Google Docs pointers
`brain gdoc "<path to .gdoc>"` prints the document id and URL. Read the content with the Google Drive or Google Docs connector (`read_file_content` / `read_doc`). Without a connector, say the content is unavailable; never guess it.

Never connect a folder inside the brain itself, and never write, rename, or delete anything under `Sources/`.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. With `sharing: git`, list the shared files changed and suggest a commit; never push or open a pull request yourself.
