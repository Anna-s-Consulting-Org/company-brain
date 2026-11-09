---
name: contribute
description: Commit improvements to the Company Brain system itself - skills, templates, commands, the engine, System/ docs, CLAUDE.md - to git and GitHub without any company content (people, teams, meetings, goals, decisions, the company's name). Use for "commit my template change", "push this skill to GitHub", "contribute an improvement to the brain", "open a pull request for the engine", or any git commit in the brain folder.
---

# Contribute a system change

Git carries the system only. This skill turns a change to the system into a commit that holds nothing about the company. Content never goes to git: it reaches teammates through the shared folder (`brain share`), and `Personal/` never leaves this machine.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root).
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded.

## What git may carry
| System (git) | Content (never git) |
|---|---|
| `.company-brain/` (skills, CLI, hooks, MCP server, specs, scaffold), `System/`, `Templates/`, `.claude/`, `.claude-plugin/`, `.github/`, `.obsidian/` settings, `CLAUDE.md`, `Home.md`, `README.md`, `brain.yaml`, `.gitignore` | `Company/`, `Teams/`, `Personal/`, `Sources/`, `Exports/`, `index.md`, `log.md`, `brain.local.yaml`, `.checkin.json`, Obsidian workspace files |

Other paths are refused until they are listed under `git.allow` in `brain.yaml` (never a content path).

## Steps
1. **See what changed**: `brain git status`. It splits changes into system (committable), content (stays out) and paths that are not system paths. If it lists content tracked by git, stop and offer `brain git untrack` (dry run first, `--yes` only after the user agrees).
2. **Keep the change generic.** A skill, template or doc must not name the company, a person, a team, a customer, or link to a note in `Company/`, `Teams/` or `Personal/`. Use placeholders (`<Team>`, `[[Jane Doe]]` style examples, `{{COMPANY}}` in scaffold files) and `TBD`. Shipped docs carry no fixed dates: keep `date: {{TODAY}}` in `System/` and `Home.md`.
3. **Keep the engine consistent** when the change touches these:
   - `System/`, `Templates/`, `CLAUDE.md`, `Home.md`, `.gitignore`, `.obsidian/`: run `brain scaffold-sync` so new brains get it.
   - Engine code or skills: `python3 -m pytest .company-brain/tests -q` (needs `pytest`).
   - Always: `brain check --severity error`, `brain freshness`, `brain upstream-check --verify` (files vendored from obsidian-second-brain must stay unedited).
4. **Stage system files only**: `brain git stage`. It adds every changed system file and nothing else, then runs the guard. If it reports problems (a person's name, the company name, a link or path to company content, a content note inside `System/`), fix the file, or unstage it with `git restore --staged <path>`.
5. **Show the user** `git diff --cached --stat` and a proposed commit message (what changed in the system and why). Commit only on their yes: `git commit -m "<message>"`. The pre-commit guard runs `brain git check --staged` and refuses content.
6. **Push or open a pull request only when the user asks for it in this conversation.** Show the command (`git push -u origin <branch>`) or run it on their word. CI repeats the checks and runs `brain git check --tracked` on every tracked file.

## Always
- Never stage with `git add -A`, `git add .` or `git commit -a` in the brain folder: they would pick up anything a future `.gitignore` change exposes. Use `brain git stage`, or name system paths one by one.
- Never bypass the guard (`--no-verify`) to commit content. If the guard is wrong about a genuine system file, add its path to `git.allow` in `brain.yaml` as part of the same change and say why. If it flags a name that is public on purpose (the maintainer in `LICENSE`, a plugin author), add the name to `git.public_names` in `brain.yaml`, only on the user's yes.
- A change that improves a note for this company (an objective, a meeting, a person) is content, not a system change: write it in its layer and let the shared folder carry it.
- Never push, open a pull request, or send a message on your own.
