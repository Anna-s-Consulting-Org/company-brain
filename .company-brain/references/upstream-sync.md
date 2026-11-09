# Upstream sync: bringing obsidian-second-brain changes into Company Brain

How to take what obsidian-second-brain (upstream) adds or changes and fit it to this repository. Upstream is a personal vault, and Company Brain is a company brain with three layers. A file copied as-is works only for the few scripts and rules that know nothing about layers. Everything else is adapted: it is rewritten to follow this repository's rules. This playbook is for whoever maintains the engine (a person, or an agent asked to "sync with upstream"). Operating the brain does not need it. In Claude Code in the Company Brain repository, `/upstream-sync` runs this loop and stops for your yes at each decision (it is a maintainer command in `.claude/commands/`, not shipped to new brains).

## What is tracked

`.company-brain/upstream.json` records everything taken from upstream:

- `files`: borrowed files, each `copy` (vendored byte for byte, checksum in `sha256`, never edited here) or `adapt` (ours to edit). `commit` is the upstream commit they were last synced to.
- `commands.map`: every upstream command (`commands/<name>.md`) with a decision:
  - `adapted`: a skill here was written from it (`skill` names it);
  - `covered`: an existing skill already does its job (`skill`, optional `note`);
  - `deferred`: relevant, not ported yet (`reason`);
  - `declined`: not for a company brain (`reason`).
- `commands.commit`: the upstream commit at which the commands were last triaged.

## The loop

1. **See what changed**: `./brain upstream-check`. It fetches upstream into a git remote of its own, `osb-upstream` (never `upstream`, which in a fork of this template usually names the template), and reports borrowed files that changed and, for commands, those not triaged yet, those removed upstream, and adapted or covered ones that changed since triage. `--diff` prints the changes.
2. **Copy files**: `./brain upstream-check --copy` takes the changed `copy` files as they are and updates their checksums. Run the tests: a vendored test may need a new skip in `tests/conftest.py` if it assumes upstream's layout. A skip is not allowed to hide a real failure.
3. **Port adapted files** by hand: read the diff, apply what fits, keep what is ours (layers, `brain.yaml` lookup, the CLI).
4. **Triage new commands** (below) and record each decision in `commands.map`.
5. **Follow changed commands**: for each adapted or covered command that changed, read the diff and port what improves its skill. Write nothing that breaks a rule below.
6. **Removed upstream**: delete the entry from `commands.map`. The skill here stays; it is ours. If upstream moved its commands to another folder, `upstream-check` says the folder is missing: set `commands.dir` to the new folder, then triage as usual.
7. **Record the sync**: `./brain upstream-check --mark`. It refuses, before copying or writing anything, while a command is untriaged, a removed one is still listed, or the commands folder cannot be found.
8. **Finish**: run the checks below, list the changed files, and suggest a commit. Never push or open a pull request without being asked.

## Triage: does a new command belong here?

Ask in this order and record the first answer that fits:

1. **Does an existing skill already do it?** Then mark it `covered` with that skill. If the upstream command does it better, port the improvement into the skill.
2. **Would a company, a team, or one person working in a company use it on shared knowledge?** Daily rhythm, decisions, meetings, OKRs, projects, search, capture, reviews: yes. Tools for one person's private thinking, web or social media research, codebase notes, or bots this engine does not ship: no. Mark it `declined` with the reason.
3. **Does it need API keys, services, or scripts that are not vendored?** Mark it `deferred` with what is missing, unless it can work through a connector or the `brain` CLI instead.
4. **Otherwise adapt it** as a new skill, named for what it does here (drop the `obsidian-` prefix; check the name is free among `.company-brain/skills/`).

## Adapting a command into a skill

Start from a draft: `./brain upstream-check --draft <command>` (add `--as <name>` when the default name, the command without its `obsidian-` prefix, is taken). It writes `.company-brain/skills/<name>/SKILL.md` with the front matter (description, `Use for` from upstream's English triggers, `argument-hint`), the standard sections, an adaptation checklist, and upstream's steps with the mechanical swaps done: upstream folders and references mapped to this brain's, `obsidian_search` to `brain search`, upstream commands to the skills they became, vendored scripts to `python3 "<engine>/scripts/..."`, ASCII punctuation. Whatever it cannot map (a folder this brain does not have, a script that is not vendored, a command with no skill, leftover non-ASCII text) it marks `TODO(upstream-sync)` on that line, or under the closing fence for a line inside a code block, so the code stays runnable; what the description could not map goes on the checklist. It never decides layers or approvals: that is the part you finish. Until it is finished the draft carries `disable-model-invocation: true`, so Claude never starts it on its own; `./brain commands` writes no command for it and the brain MCP server does not offer it. A test fails while any skill still holds a marker. `--draft` runs on its own: run the check, `--copy` and `--mark` separately.

The finished skill:

- **Front matter**: `name: <name>`, a `description` that says what it does and ends with `Use for "...", "..."` trigger phrases, and `argument-hint: "..."` when it takes arguments. Quote the hint.
- **Body**: a short purpose paragraph, then the same `## Before you start` and `## Always` sections every other skill has (the draft copies them from an existing skill), with the steps in `## Steps` between them. Delete the draft's first paragraph, its adaptation checklist and the `disable-model-invocation` line once every item is done.
- **Rewrite for this brain**, never copy upstream paths or tools:

  | Upstream | Here |
  |---|---|
  | `_CLAUDE.md`, folder map, `wiki/` folders | `CLAUDE.md`, `.company-brain/references/schemas.md` (folders and names by type) |
  | `Ideas/`, `Tasks/`, `Daily/` | `Personal/Notes/`, `Personal/My Board.md`, `Personal/Daily/` (via `brain new` and `brain period`) |
  | `obsidian_*` MCP tools, `vault_ops` calls | the `brain` CLI, file tools, or the brain MCP server's `brain_*` tools |
  | `uv run scripts/<x>.py` | `python3 "<engine>/scripts/<x>.py"` for vendored scripts only |
  | one vault, one owner | three layers: say which layer every write goes to |

- **Layers**: personal by default; shared (team or company) only with the user's yes; never a link from a shared note to a personal one; `## Private` never leaves its note; connector data lands in personal notes (`references/layers.md`).
- **Notes it writes** follow `references/ai-first-rules.md` and `references/schemas.md`, and `references/propagation.md` for what else to update. Fast-changing facts are dated (`references/freshness-policy.md`).
- **ASCII punctuation** (hyphens, straight quotes) and no hard-coded dates or years in the skill text.
- **Never invent facts**: unknowns are `TBD`; quotes are proven with `scripts/verify_quotes.py` where a skill relies on them.

Then wire it in:

1. Add the name to the list in `CLAUDE.md` section 4 and a row to the catalog in `System/Skills.md`; update the skill count in `README.md`.
2. `./brain commands` writes its `/company-brain:<name>` project command; `./brain scaffold-sync` copies the changed shared files into the scaffold. Front matter values must each sit on one line (plain, single-quoted or double-quoted); `./brain commands` stops on anything else.
3. Record the decision in `upstream.json` `commands.map` as `adapted` with `skill`.
4. If the skill names a script, the script must exist in `.company-brain/scripts/` (a test checks).

## Checks before you finish

```bash
python3 -m pytest .company-brain/tests -q
./brain upstream-check --verify
./brain commands --check
./brain scaffold-sync --check
./brain freshness
./brain check --severity error
```
