# Propagation rules

Adapted from the obsidian-second-brain write rules (MIT, (c) 2026 Eugeniu Ghelbur): never create a note in isolation. Every write has ripple effects; trace them forward before finishing. Company Brain adds one constraint to every ripple: **propagate up or sideways, never down** (see `layers.md`). A shared note is never edited to point at a personal note.

## Ripple table

| When this happens | Also update |
|---|---|
| Objective or KR created | the OKRs hub of its layer (Dataview picks it up; check the filename pattern), its `parent:` objective's `## Supporting objectives` list, `brain refresh` (OKR tree) |
| KR check-in | the KR's inline fields, one row in the objective's `## Check-ins`, `last_checkin:` and `status:` on the objective, the author's weekly note (`## KR check-ins`) |
| Project created | the layer board (a card in Backlog or the column that matches status), the KR(s) it serves (`## Supporting projects`), the roadmap if `roadmap:` is set, today's daily note if personal |
| Solution or opportunity created | its `parent:` note's `## Children` list, `brain refresh` (OST views and the prioritization matrix) |
| Solution status changes to planned or building | roadmap board card (Now or Next), and a project note if work starts |
| Meeting note written | each action item goes to the owner's board (your own items to `Personal/My Board.md`, team commitments to the team board), each decision gets a decision record when it is significant, attendees' stakeholder notes (`Personal/Stakeholders/`) get `last_interaction:` and new open asks, and a shared meeting that shows who owns or works on a project goes to `brain person works-on` |
| Decision recorded | the note it came from (`## Decisions`), the project or OKR it affects, `supersedes:` on the replaced decision |
| Person profile created or changed | team hub members (Dataview), `brain refresh` (org chart, Works on blocks, the Organization map), never a personal 1:1 or stakeholder note's content |
| Work seen in a connected system (a lead, owner, or contributor on a project) | `brain person works-on` on the person's profile at or above the confidence threshold (the rest listed for the user to confirm), the project note's `refs:` when the system id is new, `brain refresh` |
| Project created or its People changed | `brain refresh` (each named person's Works on block); a project made from an Organization "no project note yet" entry gets the system id in `refs:` |
| Stakeholder note created or changed | nothing shared; `My Stakeholders.md` picks it up (Dataview) |
| Personal weekly written | `Personal/My Board.md` (action items), KR check-ins on the objectives the user owns, a drafted team update (proposed, not written, until the user approves) |
| Team update written | the team roll-up for that week, if one already exists (`## Updates` list) |
| Any write | `brain index` at the end of the skill run (rebuilds `index.md`); append one line to `log.md` |

## Kanban card format

Same as obsidian-second-brain:

```markdown
- [ ] 🔴 **Title** · @{YYYY-MM-DD}
	One line of context. [[Project]] [[Owner]]
```
Priority: 🔴 blocking or this-week critical, 🟡 important, 🟢 nice to have. Done cards move to the Done column as `- [x] ~~**Title**~~ ✅ Oct 22` and are never deleted.

## Stubs

If a link target does not exist, create a stub in the right layer (frontmatter, title, `## For future agent`, one line of context) rather than leaving a dangling link. Exception: never create a stub in `Personal/` for a link from a shared note; that link should not exist.

## Archiving

Never delete notes. Set `status: archived` (or `dropped` for discovery and OKRs) and leave the file in place. Obsidian search and Dataview queries already filter on status.
