# Layers and multiplayer rules

The canonical spec for how Company Brain separates personal, team, and company knowledge. Every skill that writes to the brain resolves the target layer with this document before writing. The human-readable version for the vault is `System/Layers and privacy.md`; if the two ever disagree, this file wins.

## The three layers

| Layer | Folder | Shared with | Travels through | Typical content |
|---|---|---|---|---|
| company | `Company/` | everyone in the company | the shared folder, never git | mission, vision, values, strategy, company OKRs, plans, discovery, roadmap, org chart, people profiles, company projects, all-hands and leadership meetings, company decisions |
| team | `Teams/<Team>/` | everyone (owned and edited by the team) | the shared folder, never git | team charter, team OKRs, team projects, team meetings, team weekly updates and roll-ups, team discovery, team board and roadmap |
| personal | `Personal/` | nobody (local only) | nothing, this machine only | identity (`Me.md`), daily notes, personal weekly notes, 1:1s, stakeholder notes, private goals, personal board, inbox, drafts |

Two more folders sit beside the layers and are not layers:

- `Sources/` holds symlinks to external folders (Desktop, Google Drive). Read-only by rule, gitignored, machine-local. See `references/sources.md`.
- `System/` and `Templates/` hold the framework library, docs, and templates. They are part of the system, which travels through git (see Two channels), and are rarely edited.

The layer is recorded twice, on purpose: by the folder the note lives in (what the shared folder acts on) and by `layer:` in frontmatter (what agents and Dataview read). They must agree. `brain check` reports any note whose `layer:` does not match its folder.

## Identity

A brain has many users; each user's clone has exactly one `Personal/Me.md`. It is the identity record every skill reads first:

```yaml
---
type: me
person: "[[Jane Doe]]"        # links to the shared profile Company/Org/People/Jane Doe.md
teams: ["[[Platform]]"]       # team hubs this person belongs to
role: "Engineering Manager"
manager: "[[Sam Lee]]"
timezone: UTC
---
```

"Me" in any skill means the person in `Me.md`. "My team" means the first entry of `teams:` unless the user names another. If `Me.md` is missing, run `/company-brain:setup` (or `brain init`) before writing anything.

## Direction of links (the leak rule)

Links may point **up** the stack, never **down**:

```
Personal  ──links to──▶  Team  ──links to──▶  Company
    ▲                        ✕                    ✕
    └──── no shared note may link to a Personal note
```

- A personal note may link to anything.
- A team or company note may link to team and company notes only. A wikilink or embed from `Company/` or `Teams/` to a note in `Personal/` is a leak: for everyone else it is a dangling link, and its title alone can reveal private content (a 1:1 title, a draft decision).
- Dataview queries in shared notes may read `Personal/` (each person's query runs over their own local data). The leak rule applies to static links, not to code blocks.
- A team note may link to another team's notes. Teams are visible to the whole company; there is no team-private layer by default. A team that needs privacy uses a separate brain or a restricted Drive folder mounted as its team folder (see Sharing models).

Enforced by: the `layer_guard` hook on every write, and `brain check` across the whole vault.

## Private sections

Inside a personal note, everything under a `## Private` heading (to the next heading of the same or higher level) is never copied into a shared note by any skill, including `/company-brain:promote`. Use it for candid notes in 1:1s, feedback drafts, and personal reflections.

## Promotion (personal to team to company)

Moving knowledge up the stack is always a deliberate, user-approved step:

1. The user asks to share, publish, or promote a note, or a skill's final step proposes it (the weekly skill proposes a team update).
2. The `promote` skill builds the shared version: drops `## Private` sections, rewrites links to `Personal/` notes as plain text, sets `layer:` and `team:`, and removes personal-only frontmatter (`energy`, `mood`).
3. The user sees the diff and confirms.
4. The shared note is written in the target layer. The personal note gets `promoted_to: "[[Shared note]]"` (an upward link, allowed). The shared note never records the personal note's path.

Nothing is ever promoted automatically by a hook, scheduled job, or background agent.

## Connector data and people

Data from connectors lands in personal notes and reaches a shared note only as content the user approved. One narrow exception: who works on which project. When a company-visible record (a project tracker, a code host, a shared doc, a shared channel or meeting) shows that a colleague leads, owns, or contributes to a project, `brain person works-on` records it on their shared profile. The command needs a source, refuses anything below `people.works_on_min_confidence` in `brain.yaml` (default `high`), and refuses a source that links to a Personal note. Evidence that exists only in a DM, an email, a private channel, a private calendar event, or a 1:1 never reaches a profile without the user's yes. With `sharing: git` the change still waits for the user's commit or pull request.

A profile shows the person as the company sees them: role, team, manager, contact, and the work they do. Stakeholder management (what they care about, how we can help each other, how to work with them, open asks, relationship, influence, interest, last interaction, follow-up, candid notes) lives only in `Personal/Stakeholders/Stakeholder - <Full Name>.md`. Those sections and fields on a profile are an error in `brain check` and the layer guard. A profile's `## My notes on them` is a Dataview query over the reader's own Personal/ folder, so each reader sees only their own notes and the shared file links nowhere private.

## Conflict-free multiplayer writes

When several people write to the same shared area, structure the files so that two people never edit one file at the same time (a shared folder keeps both versions as separate copies instead of merging them):

- **Weekly updates**: each person writes their own file `Teams/<Team>/Weekly/<YYYY>-W<WW> - <Team> - <Person>.md`. The team roll-up `... - <Team> - Team Weekly.md` is written by one person (the lead or whoever runs `/company-brain:team-weekly`).
- **KR check-ins**: the KR owner edits only their own KR line in the objective note, and appends one row to its `## Check-ins` table. Line-level changes by different owners merge cleanly.
- **Meetings**: one note per meeting, written by the note-taker. Other attendees add to it through a follow-up edit, not a second note.
- **Boards**: one board per team. Personal action items go on `Personal/My Board.md`, not on the team board, unless they are team commitments.
- **Generated views** (`OKR Tree`, `Prioritization`, `Org Chart`, discovery canvases) are rebuilt by `brain refresh` inside `<!-- brain:auto:... -->` markers. They can be regenerated by anyone at any time, so a conflict copy of one is resolved by deleting it and re-running `brain refresh`, never by hand.

## Two channels: content and system

A brain holds two kinds of files, and each has exactly one way to reach other people. They never mix.

| Channel | What | Travels through | Guarded by |
|---|---|---|---|
| content | every note in `Company/`, `Teams/`, `Personal/`; `Company/company.yaml` (company name, fiscal year, timezone, shared sources); `index.md`, `log.md`, `Sources/`, `Exports/`, `brain.local.yaml`, `.checkin.json` | `Company/` and `Teams/`: the shared folder (`sharing.model`). Everything else: nowhere, it stays on this machine | `.gitignore`; `brain check` (Personal/ inside a shared or synced folder, links not reachable) |
| system | `.company-brain/` (engine, skills, hooks, CLI, MCP server, specs, scaffold), `System/`, `Templates/`, `CLAUDE.md`, `Home.md`, `README.md`, `brain.yaml`, `.gitignore`, `.claude/`, `.claude-plugin/`, `.github/`, `.obsidian/` settings | git (a GitHub repository, for example) | the pre-commit guard `brain git check --staged`, CI `brain git check --tracked` |

**Git carries the system only.** A commit may hold system paths (the list above, plus `git.allow` in `brain.yaml`) and nothing else. The guard refuses:
- any path in `Company/`, `Teams/`, `Personal/`, `Sources/`, `Exports/`, and the local files above, whatever `git.allow` says;
- any path that is not a system path;
- a note with a content type (objective, meeting, person, decision, ...) inside `System/` or at the root, or inside `Templates/` without template syntax;
- added lines in system files that contain the company's name, a person's full name (from `Company/Org/People/`), a link to a company note, or a path into a real team's folder or to a content note.

Deleting tracked content from git always passes: that is how an older brain, which shared notes through git, moves to this model (`brain git untrack`). Nothing reviews a commit for meaning, so the `contribute` skill also asks the author to keep system files generic: placeholders, not names.

## Sharing models (content)

| Model | How `Company/` and `Teams/` travel | Personal layer | When to use |
|---|---|---|---|
| `drive` | symlinks into a folder in a Google Shared Drive (Drive for Desktop, mirror mode recommended) | a normal local folder | Most companies. No review step, so keep company-layer edits to a few editors (Drive permissions) |
| `folder` | symlinks into any other folder everyone can reach: OneDrive, Dropbox, iCloud, a network share | a normal local folder | Companies on another sync service |
| `local` | not shared | local | Trying the system alone before inviting the team |

`brain share --to <folder>` sets it up: a dry run first, then `--yes` moves `Company/` and `Teams/` into the folder (or, when the folder already holds them, keeps the shared copy and moves this machine's copy to `.share-backup/`), replaces them with links, and records the model and the folder in `brain.local.yaml`. The shared folder must sit outside the brain, and the brain must not sit inside it, so `Personal/` can never sync. Each teammate runs the same command with their own path to the same folder.

The model is this machine's choice, recorded in `brain.local.yaml` under `sharing.model`; company settings that teammates need are in the shared `Company/company.yaml`. After a shared-layer write, skills say whether it syncs now (`drive`, `folder`) or stays local (`local`), and never suggest a commit. There is no pull request for content, so a change to a company note is shown as a diff and written only after the user's yes. Skills never run `git push` and never open a pull request on their own.

Older brains used a `git` model that committed `Company/` and `Teams/`. It is retired: `brain init` moves the settings out of `brain.yaml` and reads `git` as `local`, and `brain check` reports tracked content as an error until `brain git untrack` removes it from git (the files stay on disk).

## What each skill writes where (summary)

| Activity | Layer by default | Override |
|---|---|---|
| Daily note, personal weekly, 1:1, private goal, inbox capture | personal | never shared directly; promote instead |
| Stakeholder note (my view of a person: relationship, influence, interest, open asks) | personal | never shared, never promoted |
| Who works on which project, from a company-visible record in a connected system | company (the person's profile, `works_on:`) | below the confidence threshold: nothing is written; the user confirms first |
| Weekly team update | team (own file) | none |
| Team roll-up, team OKRs, team meeting, team project, team board | team | company when the user says it is company-wide |
| Mission, vision, values, strategy, VPC, BMC, company OKRs, annual and quarterly plans, roadmap, org chart, people profiles, all-hands, leadership meetings | company | team when the user scopes it to one team |
| Discovery (outcomes, opportunities, solutions, experiments) | the layer of the OKR the outcome serves | as stated by the user |
| Decision record | the layer of the thing decided | as stated |
| Ingested source summary | personal unless the source is shared and the user says so | as stated |

When the layer is genuinely unclear (for example a meeting with no attendee list), ask once. Default to personal when the user does not answer: a note in the wrong private place is easy to promote; a note in the wrong shared place has already leaked.
