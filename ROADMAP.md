---
date: 2026-11-08
type: system
tags: [system, roadmap]
ai-first: true
layer: company
---

# Company Brain Roadmap

## For future agent
This note holds an honest review of Company Brain (what it does well, what it lacks) and the roadmap its owner set from that review: access for non-technical users, automation, promotable notes and skills, large organizations, and protection. The review was written on 2026-11-08 from reading the code, running the tests and checks, and testing the Drive recipe on a throwaway repository. It is not based on use by a real team, so read the strengths as design and test results, not outcomes. Every roadmap item is a plan, not a built feature: check `.company-brain/` before assuming one exists. This note is about the product, not about any company's content, so it sits at the repository root rather than in `System/`, which ships to every brain and must stay free of fixed dates.

## How the review was done
- **Read**: `README.md`, the notes in `System/`, the specs in `.company-brain/references/`, the skills, `brain.py`, `vault_ops.py`, `vault_health.py` and the CI configuration.
- **Ran**: the test suite (212 passed, 8 skipped, as of 2026-11-08), `brain check`, `brain freshness`, `brain upstream-check --verify` and `brain scaffold-sync --check`.
- **Tested**: the Drive recipe in [[Sharing models]], on a throwaway repository with a second clone standing in for a teammate.
- **Not done**: use by a real team, running the semantic index builder, and any measurement at scale.
- **Compared against**: a Maven lightning lesson on company brains by Aman Khan and Tal Raviv, known only through a secondhand written summary.

## What it does well
- **A well-specified privacy model, enforced by checks.** Three layers, links that only point up, `## Private` sections, promotion only after a diff and a yes, and connector data landing in the personal layer are all specified and enforced. A hook checks every note Claude writes, `brain check` scans the whole brain, and with git, CI runs it on every push. The limit: edits made directly in Obsidian or Drive are only caught when someone runs `brain check`, or by CI with git.
- **More than most comparable setups to stop knowledge going stale.** The freshness lint wants `as of` dates on things that change. `checkin` asks note owners whether their notes still hold, `reconcile` proves contradictions with exact quotes, decisions record what they replace, and people's history is added to, never overwritten. All of this only helps if people run these skills, which has not been observed.
- **Notes structured for an agent to find and reason over.** Fixed fields, a summary for the next agent, set folders and unique names. `brain new` refuses duplicates, and `brain refresh` regenerates the OKR trees, discovery trees, org chart and index from the notes.
- **Safe defaults for an AI working on company data.** Claude never pushes, publishes or sends anything on its own. Scheduled runs only draft. When the layer is unclear, the note goes to the personal layer. Text found in sources is treated as information, not instructions.
- **Careful engineering, and git mode is a complete package.** Tests pass, and CI also runs the brain checks, verifies the files borrowed from obsidian-second-brain are unedited, and checks the starter kit is in sync. With git, notes, skills and the engine travel together and company-wide changes go through review. Passing tests show the code does what it is written to do, not that it works for a team.

## Areas for improvement
- **Hard for non-technical colleagues to contribute.** Getting started needs Obsidian with four community plugins, the Claude Code plugin, Python, `uv` and git. The claude.ai option is a read-only snapshot someone re-exports by hand. Google Docs can only be read.
- **Drive mode is a manual recipe, not a feature.** Folders are moved and linked by hand, skills and the engine do not travel through Drive, there is no review step and no CI, conflicting copies are not detected, and finding Drive folders only works on macOS. See [[Sharing models]].
- **No route for one person's better skill or prompt to reach the team.** Notes can be promoted; skills cannot. Improving a skill means editing the engine, opening a pull request, and every teammate updating their plugin.
- **Not ready for large organizations.** One brain per company and no private team area, so leadership, HR or legal cannot use it for sensitive work. Semantic search cannot be turned on: the index builder is not in the repository, and the upstream builder would skip shared notes in Drive mode. Search reads at most 10,000 files (as of 2026-11-08), and meeting filenames can clash between teams.
- **Unproven with a real team, and a fuzzy line between product and company brain.** The public repository is both the template and a working brain, and nothing stops real company content being written into it and published. The multi-user design has only been exercised by tests.

## Principles the roadmap keeps
1. **Personal stays personal.** Nothing leaves `Personal/` without its owner's yes.
2. **People decide; the system does the rest.** Automation drafts, checks, rebuilds and syncs. Approving, publishing and promoting stay a human yes.
3. **Review for what affects everyone.** Company-layer notes and shared skills are reviewed before they reach everyone.
4. **No claim without a measurement.** Speed and scale claims wait for a test.

## Roadmap at a glance
Item codes refer to the sections below.

| Horizon | Items |
|---|---|
| Now | A1 check the facts the access plan depends on; D1 turn on semantic search; E1 separate the product from company brains; E3 keep `Personal/` out of anything shared; C1 test note promotion into Drive folders |
| Next | A2 a documented path for non-technical users; A3 take `uv` off that path; A4 setup installs Python when it is missing; B1 rebuild views after every write; B3 scheduled checks; B4 `brain share --drive`; C2 skill promotion; C3 skill proposals from Drive; D2 team names in filenames; D3 restricted teams; D4 measure at scale; E2 checks on every edit; E4 detect conflict copies |
| Later | B2 setup creates the schedules; B5 automatic plugin updates; B6 automatic index updates; B7 one approval inbox; C4 team skill plugins; C5 CI for skills; D5 shared search index; D6 partial mounts; D7 several linked brains; D8 administration; E5 to E7 skill review records, secret scans, backups |

## A. Access for non-technical users
**Goal**: a non-technical colleague can set up and use the brain without knowing what Python, `uv` or git are. Python stays: the engine is written in it and shares code with upstream, which is also Python. The work is to make Python install itself or come with the app, and to take everything else off the user's path.

**Why Python stays.** Every skill calls the `brain` CLI, and the Python and shell code is about 9,300 lines (as of 2026-11-08), part of it borrowed from obsidian-second-brain. Upstream needs Python too: its README lists Claude Code, `git` and `uv` ("for the Python helpers (health check, research toolkit, bootstrap)") as prerequisites. Removing Python would mean a rewrite and losing the shared code, for little gain.

**What a non-technical user needs today, and the target**

| Tool | Today | Target |
|---|---|---|
| Python | installed by hand; on a fresh Mac, `python3` first asks to install the developer tools | provided by Cowork, or installed by setup with one yes |
| `uv` | needed for the MCP server (Claude Desktop chat) | off the user's path: Cowork does not need it |
| git | needed to get and share the brain | off the user's path in Drive mode: notes through Drive, the plugin through a marketplace or the organization's catalog |
| Obsidian and four plugins | needed for hubs and boards | stays required |

- **A1 Check the facts (Now).** Does Cowork's environment include `python3`? Can the Claude app install a plugin from a GitHub marketplace on a computer without git? Can an organization publish the plugin through its claude.ai plugin catalog, so nobody installs it by hand?
- **A2 A documented non-technical path (Next).** Drive plus the Claude app, offered by the setup skill and written up in [[Setup]].
- **A3 Take `uv` off that path (Next).** Only the MCP server for Claude Desktop chat needs `uv`; Cowork users do not. Later, check whether the MCP server can ship as a one-click Claude Desktop extension.
- **A4 Setup installs Python when it is missing (Next).** Setup checks for a working `python3`, explains in one sentence why it is needed, and installs it with the user's yes (on macOS, the developer tools prompt or the python.org installer; on Windows, the python.org installer). Needed only if A1 shows Cowork does not provide it.

**Done when**: someone who has never used a terminal can, with the Claude app and Drive, run setup, daily, weekly, meeting and promote, tested on a fresh macOS and a fresh Windows computer.

## B. Automation
**Goal**: automate the mechanics; people only approve.

**What is automatic today**: the hooks on Claude's writes, and the macOS starter-kit watcher. Scheduled runs are documented in [[Automations]] but each person sets them up by hand.

**On "make everything automated".** Fully automatic publishing and promotion would break principles 1 and 2: a private note could reach the company with nobody deciding it should. The recommendation is to automate everything except the yes, and make the yes a single step (B7).

- **B1 Rebuild views after every write (Next).** A hook runs `brain index` or `brain refresh`, instead of each skill ending with it.
- **B2 Setup creates the schedules (Later).** Daily note, weekly draft, check-in, health and reconcile, created with one yes instead of copied from [[Automations]].
- **B3 Scheduled checks (Next).** `brain check` and `brain freshness` on a schedule, which stands in for CI in Drive mode.
- **B4 `brain share --drive` (Next).** Moves and links the shared folders, takes them out of git, and records the Drive paths so teammates can recreate the links. The manual recipe is in [[Sharing models]].
- **B5 Automatic plugin updates (Later).** Check whether marketplace or organization-catalog updates reach users without a manual step.
- **B6 Automatic index updates (Later).** The semantic index updates itself after `brain refresh`, re-embedding only changed notes.
- **B7 One approval inbox (Later).** Everything waiting for a yes (team updates, promotions, skill proposals, check-in questions) arrives as one message, approved with one reply.

**Always a human step**: promoting a note, publishing a team update, approving company-layer changes, merging a skill, pushing, sending messages.

## C. Promotable notes and skills
**Model**: notes travel through Drive; skills travel through git, as part of the engine.

**A note on the source.** The lesson summary recommends cloud drives over git in general; it does not split skills from notes. The split is a design choice made here, and a sound one: a skill is a set of instructions that runs for everyone, so a bad skill does more harm than a bad note. Skills deserve review and versions; notes need speed.

**Notes** can already be promoted (`/company-brain:promote`).
- **C1 Test promotion into Drive folders (Now).** Promotion writes into `Company/` or `Teams/<Team>/`, which are symlinks in Drive mode. It has not been tested there.

**Skills: proposed layers**

| Layer | Where it lives | Who uses it | How it gets there |
|---|---|---|---|
| personal | Claude's personal skills folder (`~/.claude/skills/`), which Claude Code already loads; to verify for Cowork | you | you write it, or Claude drafts it from a prompt you keep reusing |
| team | the engine repository, as a team plugin or a team prefix | the team | promotion, then review |
| company | the engine repository, core skills | everyone | promotion, then review |

**Proposed flow**
1. `brain promote-skill <name> --to team|company` makes a clean copy (no personal paths, no links or names of private notes), lints it (description, what it writes, no secrets), shows the diff and asks for a yes.
2. The proposal travels one of two ways: people who use git get a branch and the commands to push it; everyone else drops it in a proposals folder in Drive (`Teams/<Team>/Skill proposals/`) for a maintainer to pick up.
3. A maintainer reviews and merges in git; CI lints and dry-runs the skill.
4. A plugin update delivers it to everyone (B5).
5. The personal skill records where it was promoted to.

- **C2 Skill promotion command and lint (Next).**
- **C3 Skill proposals from Drive (Next).**
- **C4 Team skills as separate plugins (Later).** Open question: one plugin per team, so only that team installs it, or team-prefixed skills in the core plugin.
- **C5 CI for skills (Later).**

## D. Large organizations
**Goal**: support a company with many teams and divisions, some sensitive teams, and thousands of notes, with limits stated from measurement.

- **D1 Turn on semantic search (Now).** Bring in the upstream index builder, adapted to follow Drive links; keep the index out of git; add `brain semantic build`. A ready task description exists from the 2026-11-08 session.
- **D2 Team names in filenames (Next).** Team-layer meetings and decisions named `<YYYY-MM-DD> - <Team> - <Title>`, so two teams cannot clash.
- **D3 Restricted teams (Next).** `visibility: restricted` on a team's main note. The folder is a Drive folder only members can open, or a private repository. Open notes may not link into it (the same rule as `Personal/`), `export-pack` leaves it out, and `brain check` enforces both.
- **D4 Measure at scale (Next).** Generate test brains of 1,000, 10,000 and 50,000 notes; time search, refresh, check and index builds; write the measured limits into the docs.
- **D5 A shared search index (Later).** Build the index for `Company/` and `Teams/` once on a schedule and share it; each person adds their own `Personal/` notes locally. Move to a proper vector store if D4 shows the JSON file is too slow. A decision is needed: a cloud embedding service sends company text to that provider.
- **D6 Partial mounts (Later).** Each person links `Company/` and only their own teams; `brain check` tells "not mounted" apart from a broken link.
- **D7 Several linked brains (Later).** Division brains under a company brain, listed in `brain.yaml`, with read-only search across them. The largest item; only after D3 to D6.
- **D8 Administration (Later).** Who may edit the company layer (Drive permissions, or code owners in git), and onboarding many people at once from a directory.

## E. Protection
- **E1 Separate the product from company brains (Now).** Document that the public product repository holds placeholders only and each company's brain is a private repository (for example GitHub's "Use this template", set to Private). Add a marker in `brain.yaml` that setup clears, so `brain check` can warn when the product repository holds real content.
- **E2 Checks on every edit, not only Claude's (Next).** Setup installs a git pre-commit hook that runs `brain check --severity error`; Drive mode uses the scheduled checks from B3.
- **E3 Keep `Personal/` out of anything shared (Now).** `brain check` errors when `Personal/` sits inside a synced Drive folder or is tracked by git; the semantic index is never committed (D1).
- **E4 Detect conflict copies (Next).** `brain check` finds the duplicate files Drive keeps when two people edit one note.
- **E5 Skill review records (Later).** No unreviewed skill reaches others; record who approved each one.
- **E6 Secret scans (Later).** A scheduled scan of the whole brain, since the write hook only sees Claude's writes.
- **E7 Backups (Later).** Drive keeps limited history per file; a scheduled snapshot of the shared folders gives a restore point.
- Restricted teams (D3) are also a protection item.

## Related
- [[Sharing models]]: git, drive and local, and the manual Drive recipe
- [[Layers and privacy]]: the layer rules every item above keeps
- [[Automations]]: what runs automatically today
- [[Setup]]: install and onboarding
