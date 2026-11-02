---
name: checkin
description: Ask me whether old notes I own still hold - picks up to 3 stale project, team or person notes, shows what each says and when it was last confirmed, keeps asking until answered, then saves the news with attribution. Catches facts that never reached the brain, which no lint can see. Use for "check in", "which of my notes are out of date", "ask me about stale notes", "do my notes still hold".
---

# Check-in

A fact check compares notes with other notes. News that never reached the brain (a project that stalled, a new owner, a team that moved) leaves a note stale, and `brain freshness` cannot see it. The owner is the only source, so this skill asks them: a few notes at a time, each shown with what it says and when it was last confirmed. The helper `scripts/checkin.py` does the deterministic half (picking, cards, memory); you condense each note into facts and apply the answers.

## Before you start
1. **Find the brain.** The session context has a **Company Brain** line with the brain path and the engine path. If it is missing, run `python3 "${CLAUDE_SKILL_DIR}/../../scripts/brain.py" root`. No brain found: stop and tell the user to open Claude in the brain folder or set the plugin's vault path.
2. **`brain`** below means `python3 "<engine>/scripts/brain.py" --root "<brain>"` (or `./brain` from the brain root). **`checkin`** means `python3 "<engine>/scripts/checkin.py" --path "<brain>"`.
3. **Read the rules** in `<brain>/CLAUDE.md` unless they are already loaded, and `Personal/Me.md` for who "me" and "my team" are. No `Me.md`: run the `setup` skill first.
4. **Write only with file tools or the `brain` CLI.** Never use the obsidian-second-brain MCP tools here; they point at a different vault.

## Which notes
- Only notes **I own** (`owner:` is me), plus my own person profile and notes of the team I lead. Never ask me about, or answer for, a note another person owns; that is their check-in.
- Types: `checkin pick --types person,project,team --max-open 20`. The helper does not report the owner, so read each candidate and keep at most 3 that are mine. `--max-open 20` only widens the pool you filter; never open more than 3 cards.
- Facts to ask about are **work facts**: status, owner, scope, dates, role, team, manager. Never ask for or record health, compensation, performance or personal-life facts in a shared note (`CLAUDE.md` section 7).
- `checkin: never` in a note's frontmatter keeps it out for good. `checkin: priority` moves it to the front.

## Mode: ask (once a day)
1. `checkin pick --types person,project,team --max-open 20`. It returns notes whose facts are older than 14 days (`--days N` to change), with an excerpt. Skip closed statuses and notes I do not own.
2. For each of my notes (at most 3), read the note itself (the excerpt is a hint, not the source) and write **1 to 3 facts**: one short line each, under 140 characters, taken from the note only. Never add, guess or round a fact. Prefer facts that can change.
3. Open each card: `checkin ask --note "<path>" --fact "..." --fact "..."`.
4. `checkin message` and send its output to me **verbatim**, as one message. No commentary, no second message.

## Mode: nudge (every few hours while I am awake)
5. `checkin message`. If it prints nothing, nothing is open: send nothing. Otherwise send it verbatim; it repeats each card in full with a reminder count.

## Mode: answer (whenever I reply, even days later)
6. `checkin status` to see the open cards. Numbers in my reply refer to the last message sent; `--number N` resolves them. A reply can cover several cards (`1 same`, `2 moved to Rotterdam`, `skip 3`). If it is ambiguous, ask once which number it is for.
7. For each answer:
   - **same**: `checkin done --number N --outcome same`. This stamps `last-checked:` with today; the note stays quiet for 14 days.
   - **skip**: `checkin done --number N --outcome skipped`. Nothing is stamped.
   - **news**: update the note first, then `checkin done --number N --outcome updated`. Rewrite the stale claim where it lives; keep the old value only when it is useful history, labelled as the earlier value. Stamp the new claim `(stated by <owner> YYYY-MM-DD)` with confidence `stated`. Anything the reply leaves out is `TBD`, never guessed. Set `updated:` to today on notes whose facts changed; do not touch it on a note you only linked or formatted, or it hides from the next check-in.
8. **Propagate** as `references/propagation.md` says: a person change gets a bi-temporal `timeline:` entry (never overwrite history), a project status change gets a Status log row, and every note named in the news gets the change too, with `[[wikilinks]]` both ways. Never link from a shared note to a Personal note.
9. Check every note you wrote: `./brain freshness` and `python3 "<engine>/scripts/check_notes.py" --path "<brain>" --fix "<path>" ...` (the same AI-first check the write hook runs; it fixes banned characters and exits 1 on anything left). Fix what it reports.
10. Reply with one short line, for example `Saved: 1 same, 2 updated (Platform roadmap, new owner).` Say nothing more if cards are still open.

## Mode: status
11. `checkin status`, shown as a short list: note, date of the facts, times sent.

## Rules
- **Private channel only.** Cards and answers go only to me, never to a group chat, a team channel, a post, or a log others read. The open list lives in `<brain>/.checkin.json`, which is gitignored.
- **Short.** One message per run, at most 3 cards. The helper formats every card the same way.
- **Explicit only.** Never start a check-in because a conversation drifted near an old note. It runs when I ask or on my own schedule (`System/Automations.md`).
- **Shared notes**: `done` stamps `last-checked:` into the note, and news edits it. With `sharing: git`, list the shared files changed and suggest a commit; company-layer changes go through a pull request. Never push or open one yourself.
- Append one line to `log.md`: `## [YYYY-MM-DD] checkin <mode> | N asked, N answered, N open`. Names and facts stay out of it.

## Always
- Layers: Company/ and Teams/ are shared; Personal/ is local only (`references/layers.md`).
- AI-first notes: frontmatter with `date`, `type`, `tags`, `ai-first: true`, `layer`; a `## For future agent` preamble; `[[wikilinks]]` for every person, team, objective, and project (`references/ai-first-rules.md`, `references/schemas.md`).
- Never invent facts, numbers, dates, or people: write `TBD` and ask.
- Finish with `brain refresh` when people, projects or OKRs changed, otherwise `brain index`.
