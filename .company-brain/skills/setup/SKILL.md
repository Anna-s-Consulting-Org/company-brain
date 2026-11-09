---
name: setup
description: Set up or update the Company Brain - company name, your identity (Me.md), teams, manager, timezone, fiscal year, how content is shared (Google Shared Drive, a shared folder, or local only), the git guard for system changes, sources, and Obsidian. Use for "set up company brain", "onboard me to the brain", "add me to the brain", first run, or when a skill says Me.md is missing.
---

# Setup

Bootstrap a brain for its first user, or onboard a new teammate. Idempotent: running it again only fills gaps.

Keep the two channels apart when you explain choices (`System/Sharing models.md`):
- **Content** (`Company/`, `Teams/`: people, teams, meetings, goals, decisions, the company's settings) reaches teammates through a **Google Shared Drive** (`drive`) or **another shared folder** such as OneDrive, Dropbox or a network share (`folder`), or stays on this machine (`local`). `Personal/` never leaves this machine.
- **System** (engine, skills, templates, `System/` docs, `CLAUDE.md`) travels through **git/GitHub** only. Git never carries content: `.gitignore` leaves it out, a pre-commit guard refuses it, and CI checks every tracked file.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Steps
1. **Read the current state**: `brain whoami` and `brain check --severity warn`. Note what already exists (company name, teams, `me_file_exists`).
2. **Interview, one short question at a time** (skip anything already known; offer the obvious default):
   - Joining a brain your company already shares? Ask for the shared folder first (the Drive or shared folder that holds `Company/` and `Teams/`; `brain sources` lists detected Google Drive accounts). If yes, link it before anything else: `brain share --to "<folder>"`, show the dry run, then `--yes`. The company name, timezone and fiscal year then come from the shared `Company/company.yaml`, so skip those questions.
   - Company name (default: `company.name` from `brain whoami`).
   - Your full name, role, home team, other teams, manager. Teammates joining an existing brain pick their team from `all_teams`.
   - Timezone (default: the system timezone, else `UTC`) and the fiscal-year start month (default 1).
   - How to share content with teammates: `drive` (a Google Shared Drive folder, synced by Drive for Desktop), `folder` (any other folder everyone syncs or mounts), or `local` (try it alone first, share later). Explain in one line each. Do not offer git for content: git is only for improving the system.
   - Teams to create now (name and lead). Do not invent teams.
3. **Write**: `brain init --company "<C>" --me "<Full Name>" --role "<Role>" --team "<Home team>" [--team ...] --manager "<Manager>" --timezone <TZ> --fiscal-year-start <M>`, then `brain team add "<Team>" --lead "<Lead>"` for each extra team. Show the created files grouped by layer. Do not pass `--sharing`: a new brain starts as `local`, and a teammate who linked the shared folder in step 2 must keep the model `brain share` recorded.
4. **Purpose (optional, offer)**: if `Company/Mission.md` is still TBD, offer to draft mission, vision, and values with the `strategy` skill now or later.
5. **Sources (optional, offer)**: offer to mount Desktop or Google Drive folders with the `connect` skill (`brain sources` lists detected Drive accounts).
6. **Obsidian**: tell the user to open the brain folder as a vault. If `.obsidian/plugins/` lacks dataview, obsidian-kanban, templater-obsidian, or calendar, explain: Settings, Community plugins, turn off Restricted mode, install and enable those four. Graph colours by layer are preconfigured.
7. **Share content** (skip for `local`, or when step 2 already linked an existing share):
   - Ask for the folder: for `drive`, a folder in a Shared Drive (on macOS under `~/Library/CloudStorage/GoogleDrive-<account>/Shared drives/`); for `folder`, its path. It must be outside the brain folder.
   - `brain share --to "<folder>"` and show the dry run: `Company/` and `Teams/` move into that folder and are replaced by links. `Personal/` stays local. Run `--yes` only after the user agrees.
   - Tell them what teammates do: get the system (step 8), run this skill, and give the same shared folder when asked. Then `brain connect --sync` for shared sources.
   - Warn once: nothing reviews content in a shared folder, so limit who can edit the company folder (Drive permissions).
8. **System through git (only if the brain folder is a git repository, or the user wants to improve the system)**:
   - `brain init` installs the pre-commit guard; confirm with `brain check` (no "git guard is not installed" line) or run `brain git hook`.
   - If `brain check` reports content tracked by git (an older brain that shared notes through git), show `brain git untrack` and run `--yes` only after the user agrees; the files stay on disk. If `Company/` and `Teams/` were shared through git before, do step 7 first so teammates keep getting them.
   - If `git remote -v` is empty and they want one, show (do not run) `git remote add origin <repository URL>`. The remote holds the system only, so it can be the team's shared engine repository.
   - System changes are committed with the `contribute` skill (`brain git status`, `brain git stage`).
   - Teammates get the system by cloning that repository (or a copy of the folder) and installing the plugin.
9. **Plugin everywhere (optional)**: to use the brain from any folder or Cowork, set the plugin's `vault_path` to the brain folder (`/plugin`, Company Brain, configure).
10. `brain refresh`, then summarize: who you are in the brain, teams, where content is shared (`brain share`), and what to run next (`daily`, `weekly`, `okr`).

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only. Never link from a shared note to a Personal note, and never copy content under `## Private` out of Personal/ (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Search before create (`brain new` refuses duplicates and prints the existing path). Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when OKRs, discovery, scores, or people changed, otherwise `brain index`. Notes are content: they reach teammates through the shared folder (`sharing.model`), never through git, so never stage, commit or suggest committing them. Git is only for system changes (the `contribute` skill). Never push or open a pull request yourself.
